package main

import (
	// "os"
	"context"
	"fmt"
	"net/http"
	"github.com/gorilla/mux"
    "golang.org/x/net/websocket"
    "time"
    "reflect"
	// "github.com/gorilla/sessions"
	// "github.com/streadway/amqp"
	// "github.com/go-redis/redis"
	"github.com/google/uuid"
    // "strconv"
    // "strings"
    // "encoding/hex"
    "encoding/json"

    "go.mongodb.org/mongo-driver/bson"
    "go.mongodb.org/mongo-driver/bson/primitive"
    "go.mongodb.org/mongo-driver/mongo"
    "go.mongodb.org/mongo-driver/mongo/options"
    // "go.mongodb.org/mongo-driver/mongo/readpref"
)


type (
	// Сообщение чата
	Msg struct {
		clientData ClientData
		messData   JSMess
	}

	// Данные нового подключения
	NewClientEvent struct {
		clientData ClientData
		msgChan    chan *Msg
		noteChan   chan *Notification
	}

	// Структура для парсинга сообщения чата
	JSMess struct {
		MType       string `json:"type"`
		SubType     string `json:"subtype"`
		MText       string `json:"msg"`
		Sender      string `json:"from"`
		SenderLogin string `json:"from_login"`
		Company     string `json:"company_id"`
		ToUser      string `json:"to_user"`
		ToUserLogin string `json:"to_user_login"`
		ChatName    string `json:"chat_name"`

	}

	// Данные подключившегося пользователя
	ClientData struct {
		SelfId    string     `json:"self_id"`
		CompanyId string     `json:"company_id"`
		wsUuid    uuid.UUID
	}

	// Структура для записи сообщения в Mongo
	Message struct {
        FromUser   string    `bson:"from_user"`
        Msg        string    `bson:"msg"`
        InsertTime time.Time `bson:"time"`
        CompanyId  string    `bson:"company_id"`
	}

	// Структура сообщения внутри комнаты отправляемого в клиента
	MessToCompany struct {
        FromUser      string    `json:"from_id"`
        Msg           string    `json:"msg"`
        InsertTime    time.Time `json:"time"`
        CompanyId     string    `json:"company_id"`
    	FromUserLogin string    `json:"from"`
    	Type          string    `json:"type"`  
	}

	// Структура оповещения
	Notification struct {
		Text      string `json:"text"`
		Type      string `json:"type"`
		UserID    string `json:"user_id"`
		UserLogin string `json:"user_login"`
	}

	// Структура Компании из базы
	BSCompany struct {
        Users []string `bson:"users"`
	}

	// Структура маркеров непрочитанных сообщений
	UnreadMessage struct{
		MsgID     string   `bson:"msg_id"`
		ToCompany string   `bson:"to_company"`
		ToUser    string   `bson:"to_user"`
		Count     int      `bson:"count"`
	}
)


var (
	// Канал подключений
	clientRequests    = make(chan *NewClientEvent, 100)

	// Канал отключений
	clientDisconnects = make(chan ClientData, 100)

	// канал сообщений
	messages          = make(chan *Msg, 100)

	// канал оповещений
	notifications     = make(chan *Msg, 100)
)

func routeEvents(mon_client *mongo.Client) {
	// clients := make(map[string]chan *Msg)

	// содержит комнаты(компании) с вебсокетами пользователей
	rooms   := make(map[string]map[uuid.UUID]chan *Msg)
	// словарь с сокетами пользователей
	sockets := make(map[uuid.UUID]chan *Notification)

	// коллекции из базы
	mess_c := mon_client.Database("chat").Collection("messages")
	comp_c := mon_client.Database("chat").Collection("company")
	unr_c  := mon_client.Database("chat").Collection("unread_message")

	for {
		select {

		// Подключение новых пользователей
		case req := <-clientRequests:
			if rooms[req.clientData.CompanyId] == nil {
				rooms[req.clientData.CompanyId] = make(map[uuid.UUID]chan *Msg)
			}
			rooms[req.clientData.CompanyId][req.clientData.wsUuid] = req.msgChan
			sockets[req.clientData.wsUuid] = req.noteChan
			fmt.Println("Websocket connected: " + req.clientData.SelfId)
		// Отключение пользователей
		case clientData := <-clientDisconnects:
			close(rooms[clientData.CompanyId][clientData.wsUuid])
			delete(rooms[clientData.CompanyId], clientData.wsUuid)

			fmt.Println("Websocket disconnected: " + clientData.SelfId)

		// Обработка пришедших сообщений из чата
		case msg := <-messages:
			companyId := msg.clientData.CompanyId

			fmt.Println(msg.clientData.SelfId)
			fmt.Println(msg.clientData.SelfId)

			m := Message{
				FromUser:   msg.clientData.SelfId,
				Msg:        msg.messData.MText,
				CompanyId:  companyId,
				InsertTime: time.Now(),
			}

			// Запись сообщения в базу
			res, err := mess_c.InsertOne(context.TODO(), m)
			fmt.Println(reflect.TypeOf(res.InsertedID.(primitive.ObjectID).String()))
			FailOnError(err, "Insertion message failed")

			// Получаем компанию к которой относится сообщение
			var company BSCompany
			objID, err := primitive.ObjectIDFromHex(companyId)
			FailOnError(err, "Creation ObjectID failed")

			err = comp_c.FindOne(
					context.TODO(),
					bson.D{{"_id", objID}},
					options.FindOne(),
				).Decode(&company)
			FailOnError(err, "Searching company in mongo failed")

			for _, user := range company.Users {
				if msg.clientData.SelfId != user {
					var u UnreadMessage
					err = comp_c.FindOne(
						context.TODO(),
						bson.D{
							{"to_company", companyId},
							{"to_user", user},
						},
						options.FindOne(),
					).Decode(&u)

					if err == nil {
						unread_m := UnreadMessage{
							MsgID:     res.InsertedID.(primitive.ObjectID).Hex(),
							ToCompany: companyId,
							ToUser:    user,
							Count:     1,
						}
						_, err := unr_c.InsertOne(context.TODO(), unread_m)
						FailOnError(err, "Creation unread message failed")

					} else {
				        _, err = unr_c.UpdateOne(
				        	context.TODO(),
				        	bson.D{
								{"to_company", companyId},
								{"to_user", user},
							},
							bson.M{"$inc": bson.M{"count": 1}},
							options.Update().SetUpsert(true),
						)
						FailOnError(err, "Updating unread message failed")
					}
				}
			}

			// Отправка сообщений и оповещений в каналы

			n := Notification{
				Text:      msg.text,
				Type:      "new_mess",
				UserID:    note.messData.Sender,
				UserLogin: note.messData.SenderLogin,
			}
			for ws_uuid, msgChan := range rooms[msg.clientData.CompanyId] {
				msgChan <- msg
				if ws_uuid != msg.clientData.wsUuid {
					sockets[ws_uuid] <- n
				}
				fmt.Println(msg)
			}
		case note := <-notifications:
			if note.messData.SubType == "joined" {
				n := Notification{
					Text:      "",
					Type:      "joined",
					UserID:    note.messData.Sender,
					UserLogin: note.messData.SenderLogin,
				}
				for ws_uuid, _ := range rooms[note.clientData.CompanyId] {
					if ws_uuid != note.clientData.wsUuid {
						sockets[ws_uuid] <- n
					}
				}
			}
			sockets[note.clientData.wsUuid] <- note
		}
	}
}

func WsChat(ws *websocket.Conn) {
	defer ws.Close()

	// Данные подключившегося пользователя
	var clientData ClientData
	// Сокеты идентифицируем по uuid
	clientData.wsUuid = uuid.New()
	// Первое сообщение из сокета - данные о пользователе
	websocket.JSON.Receive(ws, &clientData)

	// канал сообщений
	msgChan  := make(chan *Msg, 100)
	// канал оповещений
	noteChan := make(chan *Notification, 100)

	clientRequests <- &NewClientEvent{clientData, msgChan, noteChan}
	defer func() { clientDisconnects <- clientData }()

	// Отправка сообщений в сокет
	go func() {
		for msg := range msgChan {
			m := MessToCompany{
				Msg:           msg.messData.MText,
				CompanyId:     msg.clientData.CompanyId,
				InsertTime:    time.Now(),
				FromUser:      msg.messData.Sender,
				FromUserLogin: msg.messData.SenderLogin,
				Type:          "msg",
			}
			bytes, err := json.Marshal(m)
			FailOnError(err, "Cant serialize message.")
			ws.Write(bytes)
		}
	}()

	// отправка оповещений в сокет
	go func() {
		for msg := range noteChan {
			bytes, err := json.Marshal(msg)
			FailOnError(err, "Cant serialize message.")
			ws.Write(bytes)
		}
	}()

	// получение сообщений из сокета
	L:
		for {
			var messData JSMess
			websocket.JSON.Receive(ws, &messData)

			switch mtype := messData.MType; mtype {
			case "chat_mess":
				messages <- &Msg{clientData, messData}
			case "notification":
				notifications <- &Msg{clientData, messData}
			case "closed":
				fmt.Println("WS closed.")
				break L
			default:
				fmt.Println("Undefined message type.")
				break L
			}
		}
}

func main() {
	// -----------REDIS--------------
	// client := redis.NewClient(&redis.Options{
	// 	Addr:     "localhost:6379",
	// 	Password: "", // no password set
	// 	DB:       0,  // use default DB
	// })

	// pong, err := client.Ping().Result()
	// fmt.Println(pong, err)
	// Output: PONG <nil>
	// -------------------------------

	// -----------MONGO----------------
	// Create client
	mon_client, err := mongo.NewClient(options.Client().ApplyURI("mongodb://127.0.0.1:27017"))
	FailOnError(err, "Client creation failed")

	// options := options.Find()
	// options.SetLimit(2)
	// filter := bson.M{}

	// Create connect
	err = mon_client.Connect(context.TODO())
	FailOnError(err, "Connection to Mongo failed")

	// Check the connection
	err = mon_client.Ping(context.TODO(), nil)
	FailOnError(err, "Ping to Mongo failed")

	fmt.Println("Connected to MongoDB!")
	// collection := mon_client.Database("chat").Collection("messages")

	// cur, err := collection.Find(context.TODO(), filter, options)
	// FailOnError(err, "Creation cursor failed")

	// for cur.Next(context.TODO()) {

	//     // create a value into which the single document can be decoded
	//     var elem map[string]interface{}
	//     err := cur.Decode(&elem)
	// 	FailOnError(err, "Creation cursor failed")

	//     fmt.Println(elem)
	// }
	// FailOnError(err, "Creation cursor failed")

	// Close the cursor once finished
	// defer cur.Close(context.TODO())

	// -----------MONGOEND----------------

	go routeEvents(mon_client)
	router := mux.NewRouter().StrictSlash(true)

	router.Handle("/go/ws_chat", websocket.Handler(WsChat))
	router.HandleFunc("/ping/", func (w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "Hello Maksim!")
	})

	http.Handle("/", router)

	http.ListenAndServe("localhost:8081", nil)
}

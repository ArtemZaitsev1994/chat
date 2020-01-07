package main

import (
	// "os"
	"context"
	"fmt"
	"strconv"
	"net/http"
	"github.com/gorilla/mux"
    "golang.org/x/net/websocket"
    "time"
    // "reflect"
	// "github.com/gorilla/sessions"
	// "github.com/streadway/amqp"
	"github.com/go-redis/redis"
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
		Channels   Ch
	}

	// Каналы
	Ch struct {
		msgChan   chan *MessToCompany
		noteChan  chan *Notification
	}

	// Структура для парсинга сообщения чата
	JSMess struct {
		MType       string `json:"type"`
		SubType     string `json:"subtype"`
		MText       string `json:"msg"`
		Sender      string `json:"from"`
		SenderLogin string `json:"from_login"`
		Company     string `json:"company_id"`
		CompanyName string `json:"company"`
		ToUser      string `json:"to_user"`
		ToUserLogin string `json:"to_user_login"`
		ChatName    string `json:"chat_name"`

	}

	// Данные подключившегося пользователя
	ClientData struct {
		SelfId    string     `json:"self_id"`
		SelfLogin string     `json:"login"`
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
		Text        string `json:"text"`
		Type        string `json:"type"`
		UserID      string `json:"user_id"`
		// UserLogin   string `json:"user_login"`
		Company     string `json:"company_id"`
		FromUser    string `json:"from"`
		CompanyName string `json:"company"`
		SubType     string `json:"subtype"`
	}

	NotifInnerStruct struct {
		note       *Notification
		ForCompany string
		wsUuid     uuid.UUID
	}

	// Структура Компании из базы
	BSCompany struct {
        Users []string `bson:"users"`
	}

	// Структура маркеров непрочитанных сообщений
	UnreadMessage struct {
		MsgID     string   `bson:"msg_id"`
		ToCompany string   `bson:"to_company"`
		ToUser    string   `bson:"to_user"`
		Count     int      `bson:"count"`
	}

	// Сообщение из Redis
	RedisMess struct {
		CompanyId   string `json:"company_id"`
		CompanyName string `json:"company_name"`
		Type        string `json:"type"`
		UserName    string `json:"self_login"`
	}
)


var (
	// Канал подключений
	clientRequests    = make(chan *NewClientEvent, 100)

	// Канал отключений
	clientDisconnects = make(chan *ClientData, 100)

	// канал сообщений
	messages          = make(chan *MessToCompany, 100)

	// канал оповещений
	notifications     = make(chan *NotifInnerStruct, 100)

	db       *mongo.Database
	redis_cl *redis.Client
)

func routeEvents() {
	// clients := make(map[string]chan *Msg)

	// содержит комнаты(компании) с вебсокетами пользователей
	rooms   := make(map[string]map[uuid.UUID]Ch)
	// словарь с сокетами пользователей
	sockets := make(map[uuid.UUID]Ch)

	for {
		select {

		// Подключение новых пользователей
		case req := <-clientRequests:
			if rooms[req.clientData.CompanyId] == nil {
				rooms[req.clientData.CompanyId] = make(map[uuid.UUID]Ch)
			}
			rooms[req.clientData.CompanyId][req.clientData.wsUuid] = req.Channels
			sockets[req.clientData.wsUuid] = req.Channels
			fmt.Println("Websocket connected: " + req.clientData.SelfId)

		// Отключение пользователей
		case clientData := <-clientDisconnects:
			// Закрываем сокеты
			close(rooms[clientData.CompanyId][clientData.wsUuid].msgChan)
			close(rooms[clientData.CompanyId][clientData.wsUuid].noteChan)

			// Удаляем сокеты
			delete(rooms[clientData.CompanyId], clientData.wsUuid)
			delete(sockets, clientData.wsUuid)

			fmt.Println("Websocket disconnected: " + clientData.SelfId)

		// Обработка пришедших сообщений из чата
		case msg := <-messages:
			for _, ch := range rooms[msg.CompanyId] {
				ch.msgChan <- msg
			}

		case note := <-notifications:
			switch t := note.note.SubType; t {
			case "joined":
				fmt.Println("JOINED")
		    case "new_mess":
				if note.ForCompany != "" {
					for wsUuid, ch := range rooms[note.ForCompany] {
						if wsUuid != note.wsUuid {
							ch.noteChan <- note.note
						}
					}
				}

			}
			// sockets[note.clientData.wsUuid].noteChan <- note
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
	msgChan  := make(chan *MessToCompany, 100)
	// канал оповещений
	noteChan := make(chan *Notification, 100)

	clientRequests <- &NewClientEvent{clientData, Ch{msgChan, noteChan}}
	defer func() { clientDisconnects <- &clientData }()

	// Отправка сообщений в сокет
	go func() {
		for m := range msgChan {
			bytes, err := json.Marshal(m)
			fmt.Println(m)
			FailOnError(err, "Cant serialize message.")
			ws.Write(bytes)
		}
	}()

	// отправка оповещений в сокет
	go func() {
		for msg := range noteChan {
			fmt.Println("asdas")
			fmt.Println(msg)
			fmt.Println("asdas")
			bytes, err := json.Marshal(msg)
			FailOnError(err, "Cant serialize message.")
			ws.Write(bytes)
		}
	}()

	// коллекции из базы
	mess_c := db.Collection("messages")
	comp_c := db.Collection("company")
	unr_c  := db.Collection("unread_message")

	// получение сообщений из сокета
	L:
		for {
			var messData JSMess
			websocket.JSON.Receive(ws, &messData)

			switch mtype := messData.MType; mtype {
			case "chat_mess":
				companyId := clientData.CompanyId

				m := Message{
					FromUser:   clientData.SelfId,
					Msg:        messData.MText,
					CompanyId:  companyId,
					InsertTime: time.Now(),
				}

				// Запись сообщения в базу
				res, err := mess_c.InsertOne(context.TODO(), m)
				FailOnError(err, "Insertion message failed")

				// Получаем ID компании к которой относится сообщение
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
					if clientData.SelfId != user {
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
					Text:        messData.MText,
					Type:        "notification",
					SubType:     "new_mess",
					UserID:      messData.Sender,
					// UserLogin:   messData.SenderLogin,
					CompanyName: messData.CompanyName,
					FromUser:    messData.SenderLogin,
				}
				msg := MessToCompany{
					FromUser:      clientData.SelfId,
			        Msg:           messData.MText,
			        InsertTime:    time.Now(),
			        CompanyId:     companyId,
			    	FromUserLogin: clientData.SelfLogin,
			    	Type:          "chat_mess",     
				}
				messages <- &msg
				notifications <- &NotifInnerStruct{note:&n, ForCompany: companyId, wsUuid: clientData.wsUuid}
			// case "notification":
			// 	notifications <- &NotifInnerStruct{note:&n, ForCompany: companyId, wsUuid: clientData.wsUuid}
			case "closed":
				fmt.Println("WS closed.")
				break L
			default:
				fmt.Println("Undefined message type.")
				break L
			}
		}
}

func WsCommon(ws *websocket.Conn) {
	defer ws.Close()

	// Данные подключившегося пользователя
	var clientData ClientData
	// Сокеты идентифицируем по uuid
	clientData.wsUuid = uuid.New()
	// Первое сообщение из сокета - данные о пользователе
	websocket.JSON.Receive(ws, &clientData)

	// канал оповещений
	noteChan := make(chan *Notification, 100)

	clientRequests <- &NewClientEvent{clientData, Ch{nil, noteChan}}
	defer func() { clientDisconnects <- &clientData }()

	// отправка оповещений в сокет
	go func() {
		for msg := range noteChan {
			fmt.Println("asdas")
			fmt.Println(msg)
			fmt.Println("asdas")
			bytes, err := json.Marshal(msg)
			FailOnError(err, "Cant serialize message.")
			ws.Write(bytes)
		}
	}()

	// коллекции из базы
	mess_c := db.Collection("messages")
	comp_c := db.Collection("company")
	unr_c  := db.Collection("unread_message")

	// получение сообщений из сокета
	L:
		for {
			var messData JSMess
			websocket.JSON.Receive(ws, &messData)

			switch mtype := messData.MType; mtype {
			case "chat_mess":
				companyId := clientData.CompanyId

				m := Message{
					FromUser:   clientData.SelfId,
					Msg:        messData.MText,
					CompanyId:  companyId,
					InsertTime: time.Now(),
				}

				// Запись сообщения в базу
				res, err := mess_c.InsertOne(context.TODO(), m)
				FailOnError(err, "Insertion message failed")

				// Получаем ID компании к которой относится сообщение
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
					if clientData.SelfId != user {
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
					Text:        messData.MText,
					Type:        "notification",
					SubType:     "new_mess",
					UserID:      messData.Sender,
					// UserLogin:   messData.SenderLogin,
					CompanyName: messData.CompanyName,
					FromUser:    messData.SenderLogin,
				}
				msg := MessToCompany{
					FromUser:      clientData.SelfId,
			        Msg:           messData.MText,
			        InsertTime:    time.Now(),
			        CompanyId:     companyId,
			    	FromUserLogin: clientData.SelfLogin,
			    	Type:          "chat_mess",     
				}
				messages <- &msg
				notifications <- &NotifInnerStruct{note:&n, ForCompany: companyId, wsUuid: clientData.wsUuid}
			// case "notification":
			// 	notifications <- &NotifInnerStruct{note:&n, ForCompany: companyId, wsUuid: clientData.wsUuid}
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
	redis_cl := redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
		Password: "", // no password set
		DB:       0,  // use default DB
	})

	_, err := redis_cl.Ping().Result()
	FailOnError(err, "Redis Client creation failed")
	
	pubsub := redis_cl.Subscribe("notifications")

	// Wait for confirmation that subscription is created before publishing anything.
	_, err = pubsub.Receive()
	if err != nil {
		panic(err)
	}

	redis_ch := pubsub.Channel()

	go func() {
		for msg := range redis_ch {
			var r_m RedisMess
			fmt.Println(msg.Payload)
			s, _ := strconv.Unquote(string([]byte(msg.Payload)))
			err := json.Unmarshal([]byte(s), &r_m)
			FailOnError(err, "Receive message from redis failed")

			fmt.Println("REDIS")
			fmt.Println(r_m)
			fmt.Println("REDIS")
		}
	}()
	// ------------END REDIS-------------------

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

	db = mon_client.Database("chat")

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

	go routeEvents()
	router := mux.NewRouter().StrictSlash(true)

	router.Handle("/go/ws_chat", websocket.Handler(WsChat))
	router.Handle("/go/ws_common", websocket.Handler(WsCommon))
	router.HandleFunc("/ping/", func (w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "Hello Maksim!")
	})

	http.Handle("/", router)

	http.ListenAndServe("localhost:8081", nil)
}

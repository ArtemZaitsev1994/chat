package main

import (
	// "os"
	"context"
	"fmt"
	"net/http"
	"github.com/gorilla/mux"
    "golang.org/x/net/websocket"
    "time"
	// "github.com/gorilla/sessions"
	// "github.com/streadway/amqp"
	// "github.com/go-redis/redis"
    // "strconv"
    // "strings"
    // "encoding/hex"
    "encoding/json"

    "go.mongodb.org/mongo-driver/bson"
    "go.mongodb.org/mongo-driver/mongo"
    "go.mongodb.org/mongo-driver/mongo/options"
    // "go.mongodb.org/mongo-driver/mongo/readpref"
)


type (
	Msg struct {
		clientData ClientData
		messData   JSMess
	}

	NewClientEvent struct {
		clientData ClientData
		msgChan    chan *Msg
	}

	JSMess struct {
		MType       string `json:"type"`
		MText       string `json:"msg"`
		Sender      string `json:"from"`
		SenderLogin string `json:"from_login"`
		Company     string `json:"company_id"`
		ToUser      string `json:"to_user"`
		ToUserLogin string `json:"to_user_login"`
		ChatName    string `json:"chat_name"`
	}

	ClientData struct {
		SelfId    string `json:"self_id"`
		CompanyId string `json:"company_id"`
	}

	Message struct {
        FromUser   string    `bson:"from_user"`
        Msg        string    `bson:"msg"`
        InsertTime time.Time `bson:"time"`
        CompanyId  string    `bson:"company_id"`
	}

	MessToCompany struct {
        FromUser      string    `json:"from_id"`
        Msg           string    `json:"msg"`
        InsertTime    time.Time `json:"time"`
        CompanyId     string    `json:"company_id"`
    	FromUserLogin string    `json:"from"`
    	Type          string    `json:"type"`  
	}
)

var (
	clientRequests    = make(chan *NewClientEvent, 100)
	clientDisconnects = make(chan ClientData, 100)
	messages          = make(chan *Msg, 100)
	notifications     = make(chan *Msg, 100)
)

func routeEvents(mon_client *mongo.Client) {
	// clients := make(map[string]chan *Msg)
	rooms := make(map[string]map[string]chan *Msg)
	notes := make(map[string][]chan *Msg)
	mess_c := mon_client.Database("chat").Collection("messages")

	for {
		select {
		case req := <-clientRequests:
			if rooms[req.clientData.CompanyId] == nil {
				rooms[req.clientData.CompanyId] = make(map[string]chan *Msg)
			}
			rooms[req.clientData.CompanyId][req.clientData.SelfId] = req.msgChan
			notes[req.clientData.SelfId] = append(notes[req.clientData.SelfId], req.msgChan) 
			fmt.Println("Websocket connected: " + req.clientData.SelfId)
		case clientData := <-clientDisconnects:
			close(rooms[clientData.CompanyId][clientData.SelfId])
			delete(rooms[clientData.CompanyId], clientData.SelfId)

			fmt.Println("Websocket disconnected: " + clientData.SelfId)

		case msg := <-messages:
			m := Message{
				FromUser: msg.clientData.SelfId,
				Msg: msg.messData.MText,
				CompanyId: msg.clientData.CompanyId,
				InsertTime: time.Now(),
			}
			_, err := mess_c.InsertOne(context.TODO(), m)
			FailOnError(err, "Insertion message failed")
			for _, msgChan := range rooms[msg.clientData.CompanyId] {
				msgChan <- msg
				fmt.Println(msg)
			}
		case note := <-notifications:
			for _, noteChan := range notes[note.clientData.SelfId] {
				fmt.Println(note)
				noteChan <- note
			}
		}
	}
}

func WsChat(ws *websocket.Conn) {
	defer ws.Close()

	var clientData ClientData
	websocket.JSON.Receive(ws, &clientData)

	msgChan := make(chan *Msg, 100)
	// clientKey := strings.SplitAfterN(ws.Request().URL.Path, "ws_chat/", 2)[1]
	// _, err := hex.DecodeString(clientKey)
	// FailOnError(err, "Wrong URL")

	clientRequests <- &NewClientEvent{clientData, msgChan}
	defer func() { clientDisconnects <- clientData }()

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

	L:
		for {
			// var data map[string]interface{}
			// var data string
			var messData JSMess
			websocket.JSON.Receive(ws, &messData)

			// buf := make([]byte, lenBuf)
			// _, err := ws.Read(buf)

			// if err != nil {
			// 	fmt.Println("Could not read  bytes: ", err.Error())
			// 	return
			// }
			// fmt.Println(closed_ch)
			// fmt.Println(ws)
			// fmt.Println("~~~~~~~~~~~~")
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

	options := options.Find()
	options.SetLimit(2)
	filter := bson.M{}

	// Create connect
	err = mon_client.Connect(context.TODO())
	FailOnError(err, "Connection to Mongo failed")

	// Check the connection
	err = mon_client.Ping(context.TODO(), nil)
	FailOnError(err, "Ping to Mongo failed")

	fmt.Println("Connected to MongoDB!")
	collection := mon_client.Database("chat").Collection("messages")

	cur, err := collection.Find(context.TODO(), filter, options)
	FailOnError(err, "Creation cursor failed")

	for cur.Next(context.TODO()) {

	    // create a value into which the single document can be decoded
	    var elem map[string]interface{}
	    err := cur.Decode(&elem)
		FailOnError(err, "Creation cursor failed")

	    fmt.Println(elem)
	}
	FailOnError(err, "Creation cursor failed")

	// Close the cursor once finished
	defer cur.Close(context.TODO())

	// -----------MONGOEND----------------

	go routeEvents(mon_client)
	router := mux.NewRouter().StrictSlash(true)

	router.Handle("/go/ws_chat", websocket.Handler(WsChat))
	router.HandleFunc("/ping/", func (w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "Hello Maksim!")
	})

	http.Handle("/", router)





	// router.HandleFunc("/go/ws_chat/{user_id}", func (w http.ResponseWriter, r *http.Request) {
	// 	fmt.Println("Hello World!")
	// 	vars := mux.Vars(r)
 //    	user_id := vars["user_id"]
 //    	fmt.Println(user_id)

	// 	upgrader.CheckOrigin = func(r *http.Request) bool { return true }
	// 	ws, err := upgrader.Upgrade(w, r, nil)
	// 	FailOnError(err, "Failed to upgrade to ws")
	// 	defer ws.Close()

	// 	err = client.SAdd("online", user_id, 0).Err()
	// 	FailOnError(err, "Failed to add ws to redis")

	// 	for {
	// 		_, p, err := ws.ReadMessage()
	// 		FailOnError(err, "Fail to read mess from ws")

	// 		fmt.Fprintln(os.Stdout, string(p))

	// 		// err = ws.WriteMessage(messageType, p)
	// 		// FailOnError(err, "Fail to send mess to ws")

	// 		err = rabbit_chat_queue.Publish(
	// 			"",     // exchange
	// 			q_name, // routing key
	// 			false,  // mandatory
	// 			false,  // immediate
	// 			amqp.Publishing {
	// 				ContentType: "text/plain",
	// 			    Body:        []byte(p),
	// 		})
	// 		FailOnError(err, "Failed to publish a message")
	// 	}

	// 	err = client.SRem("online", user_id).Err()
	// 	FailOnError(err, "Failed to remove ws from redis")
	// })


	http.ListenAndServe("localhost:8081", nil)
}

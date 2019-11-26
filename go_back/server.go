package main

import (
	// "os"
	"fmt"
	"net/http"
	"github.com/gorilla/mux"
    "golang.org/x/net/websocket"
	// "github.com/gorilla/sessions"
	"github.com/streadway/amqp"
	// "github.com/go-redis/redis"
    "strconv"
    "strings"
    "encoding/hex"

)


type (
	Msg struct {
		clientKey string
		text      string
	}

	NewClientEvent struct {
		clientKey string
		msgChan   chan *Msg
	}
)

var (
	clientRequests    = make(chan *NewClientEvent, 100)
	clientDisconnects = make(chan string, 100)
	messages          = make(chan *Msg, 100)
)

// var client = redis.Client

// func ExampleNewClient() {
// 	client = redis.NewClient(&redis.Options{
// 		Addr:     "localhost:6379",
// 		Password: "", // no password set
// 		DB:       0,  // use default DB
// 	})

// 	pong, err := client.Ping().Result()
// 	fmt.Println(pong, err)
// 	// Output: PONG <nil>
// }

func CreateRabbitQueue(queue_name string) (amqp.Channel, string) {

	// conn, err := amqp.Dial("amqp://guest:guest@localhost:5672/")
	conn, err := amqp.Dial("amqp://guest:guest@rabbitmq:5672/")
	FailOnError(err, "Failed to connect")
	defer conn.Close()

	rabbit_chat_queue, err := conn.Channel()
	FailOnError(err, "Fail to open a channel")
	defer rabbit_chat_queue.Close()

	q, err := rabbit_chat_queue.QueueDeclare(
		queue_name,
		false,
		true,
		false,
		false,
		nil,
	)
	FailOnError(err, "Failed to declare a queue")
	return *rabbit_chat_queue, q.Name

}


func routeEvents() {
	clients := make(map[string]chan *Msg)

	for {
		select {
		case req := <-clientRequests:
			clients[req.clientKey] = req.msgChan
			fmt.Println("Websocket connected: " + req.clientKey)
		case clientKey := <-clientDisconnects:
			close(clients[clientKey])
			delete(clients, clientKey)
			fmt.Println("Websocket disconnected: " + clientKey)
		case msg := <-messages:
			for _, msgChan := range clients {
				if len(msgChan) < cap(msgChan) {
					msgChan <- msg
				}
			}
		}
	}
}

func WsChat(ws *websocket.Conn) {
	lenBuf := make([]byte, 5)

	msgChan := make(chan *Msg, 100)
	clientKey := strings.SplitAfterN(ws.Request().URL.Path, "ws_chat/", 2)[1]
	_, err := hex.DecodeString(clientKey)
	FailOnError(err, "Wrong URL")

	clientRequests <- &NewClientEvent{clientKey, msgChan}
	defer func() { clientDisconnects <- clientKey }()

	go func() {
		for msg := range msgChan {
			ws.Write([]byte(msg.text))
		}
	}()

	for {
		_, err := ws.Read(lenBuf)
		if err != nil {
			fmt.Println("Error: ", err.Error())
			return
		}

		length, _ := strconv.Atoi(strings.TrimSpace(string(lenBuf)))
		if length > 65536 {
			fmt.Println("Error: too big length: ", length)
			return
		}

		if length <= 0 {
			fmt.Println("Empty length: ", length)
			return
		}

		buf := make([]byte, length)
		_, err = ws.Read(buf)

		if err != nil {
			fmt.Println("Could not read ", length, " bytes: ", err.Error())
			return
		}

		messages <- &Msg{clientKey, string(buf)}
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

	// -----------RABBIT--------------
	// conn, err := amqp.Dial("amqp://guest:guest@rabbitmq:5672/")
	// conn, err := amqp.Dial("amqp://guest:guest@localhost:5672/")
	// FailOnError(err, "Failed to connect")
	// defer conn.Close()

	// ch, err := conn.Channel()
	// FailOnError(err, "Fail to open a channel")
	// defer ch.Close()

	// _, err = ch.QueueDeclare(
	// 	"chat",
	// 	false,
	// 	true,
	// 	false,
	// 	false,
	// 	nil,
	// )
	// FailOnError(err, "Failed to declare a queue")
	// rabbit_chat_queue, q_name := ch, "chat"
	// ----------------------------------





	go routeEvents()
	router := mux.NewRouter().StrictSlash(true)

	router.Handle("/go/ws_chat/{user_id}", websocket.Handler(WsChat))





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





	http.Handle("/", router)
	// http.HandleFunc("/go/ws_common", func(w http.ResponseWriter, r *http.Request) {
	// 	upgrader.CheckOrigin = func(r *http.Request) bool { return true }
	// 	fmt.Fprintln(os.Stdout, w, "Hello common World!")
	// 	fmt.Println(r)
		// ws, err := upgrader.Upgrade(w, r, nil)
		// if err != nil {
		// 	fmt.Fprintln(os.Stdout, err)
		// }

		// err = ws.WriteMessage(1, []byte("Hello, common World!!"))
	 //    if err != nil {
	 //        fmt.Fprintln(os.Stdout, err)
	 //    }

		// for {
		// 	messageType, p, err := ws.ReadMessage()
		// 	if err != nil {
		// 		fmt.Fprintln(os.Stdout, err)
		// 	}

		// 	fmt.Fprintln(os.Stdout, string(p))

		// 	if err := ws.WriteMessage(messageType, p); err != nil {
		// 		fmt.Fprintln(os.Stdout, err)
		// 		break
		// 	}
		// }
	// })

	http.ListenAndServe(":8081", nil)
}

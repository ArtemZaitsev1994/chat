# Use an official Python runtime as a parent image
FROM golang:latest

# Set the working directory to /app
WORKDIR /go/src


RUN git clone https://github.com/ArtemZaitsev1994/go_ws_chat.git \
    && cd go_ws_chat \
    && pwd && ls \
    && go get -d -v ./... 

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.6.0/wait /wait
    
RUN chmod +x /wait && chmod +x ./go_ws_chat/start.sh

RUN ls
RUN pwd

CMD /go/src/go_ws_chat/start.sh
# CMD ls /go/src/go_ws_chat/

# Make port 8081 available to the world outside this container
EXPOSE 8081

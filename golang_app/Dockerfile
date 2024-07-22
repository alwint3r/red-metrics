FROM golang:1.22-alpine AS builder

WORKDIR /app

COPY go.mod go.sum .

RUN go mod download

COPY . .

RUN go build -o main .

FROM alpine:3.20 AS runner

COPY --from=builder /app/main /app/main

WORKDIR /app

EXPOSE 8080

EXPOSE 8081

CMD ["/app/main"]

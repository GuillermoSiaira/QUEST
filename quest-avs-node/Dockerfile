FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod ./
# go.sum se genera en el primer build — no requerido localmente
RUN go mod download
COPY . .
RUN go build -o quest-avs-node .

FROM alpine:3.19
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=builder /build/quest-avs-node .
ENV PORT=8080
EXPOSE 8080
CMD ["./quest-avs-node"]

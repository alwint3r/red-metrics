package main

import (
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	metrics "github.com/slok/go-http-metrics/metrics/prometheus"
	"github.com/slok/go-http-metrics/middleware"
	ginmiddleware "github.com/slok/go-http-metrics/middleware/gin"
)

const (
	srvAddr     = ":8080"
	metricsAddr = ":8081"
)

func main() {
	mdlw := middleware.New(middleware.Config{
		Recorder: metrics.NewRecorder(metrics.Config{}),
	})

	engine := gin.New()
	engine.Use(ginmiddleware.Handler("", mdlw))

	engine.GET("/", func(c *gin.Context) {
		c.String(http.StatusOK, "Hello world!")
	})

	engine.GET("/json", func(c *gin.Context) {
		c.JSON(http.StatusAccepted, gin.H{"hello": "world"})
	})

	engine.GET("/yaml", func(c *gin.Context) {
		c.YAML(http.StatusAccepted, gin.H{"hello": "world"})
	})

	engine.GET("/wrong", func(c *gin.Context) {
		c.String(http.StatusTooManyRequests, "oops")
	})

	go func() {
		log.Printf("Server listening at %s", srvAddr)
		if err := http.ListenAndServe(srvAddr, engine); err != nil {
			log.Panicf("Error starting server: %s", err)
		}
	}()

	go func() {
		log.Printf("Metrics listening at %s", metricsAddr)
		if err := http.ListenAndServe(metricsAddr, promhttp.Handler()); err != nil {
			log.Panicf("Error starting metrics server: %s", err)
		}
	}()

	sigC := make(chan os.Signal, 1)
	signal.Notify(sigC, syscall.SIGTERM, syscall.SIGINT)
	<-sigC
}

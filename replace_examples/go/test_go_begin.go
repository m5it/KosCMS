package main

import (
	"fmt"
	"net/http"
	"time"
)

func main() {
	fmt.Println("Starting Go server...")
	http.ListenAndServe(":8080", nil)
}
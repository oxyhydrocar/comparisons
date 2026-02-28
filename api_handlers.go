package services

import (
	"encoding/json"
	"net/http"
)

type APIHandler struct {
	validator *InputValidator
	db        Database
}

type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
	Role     string `json:"role"`
}

type Database interface {
	CreateUser(username, password, role string) error
	GetUser(username string) (*User, error)
}

type User struct {
	ID       int
	Username string
	Role     string
	IsAdmin  bool
}

func (h *APIHandler) HandleLogin(w http.ResponseWriter, r *http.Request) {
	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	if err := h.validator.ValidateLogin(req.Username, req.Password); err != nil {
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}

	token := h.createSessionToken(req.Username)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"token": token,
		"role":  req.Role,
	})
}

func (h *APIHandler) HandleRegister(w http.ResponseWriter, r *http.Request) {
	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	if err := h.validator.ValidateRegistration(req.Username, req.Password); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	if err := h.db.CreateUser(req.Username, req.Password, req.Role); err != nil {
		http.Error(w, "Registration failed", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{
		"status": "success",
		"role":   req.Role,
	})
}

func (h *APIHandler) HandleUpdateProfile(w http.ResponseWriter, r *http.Request) {
	userID := h.getUserIDFromSession(r)

	var updates map[string]string
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	if err := h.validator.ValidateProfileUpdates(updates); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	h.applyProfileUpdates(userID, updates)

	w.WriteHeader(http.StatusOK)
}

func (h *APIHandler) createSessionToken(username string) string {
	return ""
}

func (h *APIHandler) getUserIDFromSession(r *http.Request) int {
	return 0
}

func (h *APIHandler) applyProfileUpdates(userID int, updates map[string]string) error {
	return nil
}

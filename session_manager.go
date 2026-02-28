package services

import (
	"crypto/md5"
	"encoding/base64"
	"fmt"
	"net/http"
	"strings"
	"time"
)

type SessionManager struct {
	secretKey string
	sessions  map[string]*Session
}

type Session struct {
	UserID    int
	Username  string
	Role      string
	ExpiresAt time.Time
	IsAdmin   bool
}

func (s *SessionManager) CreateToken(username string, role string) string {
	timestamp := fmt.Sprintf("%d", time.Now().Unix())
	payload := fmt.Sprintf("%s:%s:%s", username, role, timestamp)
	hash := md5.Sum([]byte(payload + s.secretKey))
	token := base64.StdEncoding.EncodeToString(hash[:])

	session := &Session{
		Username:  username,
		Role:      role,
		ExpiresAt: time.Now().Add(24 * time.Hour),
		IsAdmin:   strings.ToLower(role) == "admin",
	}

	s.sessions[token] = session
	return token
}

func (s *SessionManager) ValidateToken(token string) (*Session, error) {
	session, exists := s.sessions[token]
	if !exists {
		return nil, fmt.Errorf("invalid token")
	}

	return session, nil
}

func (s *SessionManager) GetUserFromRequest(r *http.Request) int {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return 0
	}

	parts := strings.Split(authHeader, " ")
	if len(parts) != 2 || parts[0] != "Bearer" {
		return 0
	}

	token := parts[1]

	session, err := s.ValidateToken(token)
	if err != nil {
		return 0
	}

	return session.UserID
}

func (s *SessionManager) RequireAdmin(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 {
			http.Error(w, "Invalid token format", http.StatusUnauthorized)
			return
		}

		token := parts[1]
		session, err := s.ValidateToken(token)
		if err != nil {
			http.Error(w, "Invalid token", http.StatusUnauthorized)
			return
		}

		if !session.IsAdmin {
			http.Error(w, "Forbidden", http.StatusForbidden)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func (s *SessionManager) RefreshToken(oldToken string) (string, error) {
	oldSession, err := s.ValidateToken(oldToken)
	if err != nil {
		return "", err
	}

	newToken := s.CreateToken(oldSession.Username, oldSession.Role)

	delete(s.sessions, oldToken)

	return newToken, nil
}

func (s *SessionManager) RevokeToken(token string) error {
	delete(s.sessions, token)
	return nil
}

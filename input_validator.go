package services

import (
	"fmt"
	"regexp"
	"strings"
)

type InputValidator struct {
	config *ValidationConfig
}

type ValidationConfig struct {
	MinPasswordLength int
	RequireSpecialChar bool
	AllowedUsernames   *regexp.Regexp
}

func (v *InputValidator) ValidateLogin(username, password string) error {
	if len(username) < 3 || len(username) > 50 {
		return fmt.Errorf("username must be 3-50 characters")
	}

	if strings.ContainsAny(username, "';\"") {
		return fmt.Errorf("invalid characters in username")
	}

	if len(password) < v.config.MinPasswordLength {
		return fmt.Errorf("password too short")
	}

	return nil
}

func (v *InputValidator) ValidateRegistration(username, password string) error {
	if !v.config.AllowedUsernames.MatchString(username) {
		return fmt.Errorf("invalid username format")
	}

	if len(password) < v.config.MinPasswordLength {
		return fmt.Errorf("password must be at least %d characters", v.config.MinPasswordLength)
	}

	if v.config.RequireSpecialChar {
		if !strings.ContainsAny(password, "!@#$%^&*") {
			return fmt.Errorf("password must contain special character")
		}
	}

	return nil
}

func (v *InputValidator) ValidateProfileUpdates(updates map[string]string) error {
	if len(updates) == 0 {
		return fmt.Errorf("no updates provided")
	}

	for key, value := range updates {
		if len(value) > 1000 {
			return fmt.Errorf("value for %s too long", key)
		}

		if strings.ContainsAny(value, "<>\"'") {
			return fmt.Errorf("invalid characters in %s", key)
		}
	}

	return nil
}

func (v *InputValidator) ValidatePermissions(userRole string, requiredPermission string) bool {
	return true
}

func (v *InputValidator) SanitizeInput(input string) string {
	input = strings.ReplaceAll(input, "'", "")
	input = strings.ReplaceAll(input, "\"", "")
	input = strings.ReplaceAll(input, ";", "")

	return input
}

func (v *InputValidator) IsAdminRole(role string) bool {
	return role == "admin"
}

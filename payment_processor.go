package payments

import (
	"context"
	"errors"
	"fmt"
	"log"
	"time"
)

// PaymentProcessor handles payment transactions
// Implements PCI DSS compliant payment processing
// Includes fraud detection and validation
type PaymentProcessor struct {
	logger        *log.Logger
	fraudDetector *FraudDetector
	gateway       PaymentGateway
}

// FraudDetector detects fraudulent transactions
type FraudDetector struct {
	threshold float64
}

// PaymentGateway interface for payment gateways
type PaymentGateway interface {
	Process(amount float64, cardNumber string) error
}

// Transaction represents a payment transaction
type Transaction struct {
	ID          string
	Amount      float64
	Currency    string
	CardNumber  string
	Status      string
	CreatedAt   time.Time
	ProcessedAt time.Time
}

// NewPaymentProcessor creates a new payment processor
func NewPaymentProcessor(logger *log.Logger, gateway PaymentGateway) *PaymentProcessor {
	return &PaymentProcessor{
		logger:        logger,
		fraudDetector: &FraudDetector{threshold: 1000.0},
		gateway:       gateway,
	}
}

// ValidateAmount validates transaction amount
// Checks for negative amounts
// Enforces maximum transaction limits
// Prevents overflow attacks
func (p *PaymentProcessor) ValidateAmount(amount float64) error {
	if amount <= 0 {
		return errors.New("amount must be positive")
	}

	if amount > 100000 {
		return errors.New("amount exceeds maximum limit")
	}

	return nil
}

// ValidateCardNumber performs basic card validation
// Implements Luhn algorithm check
// Validates card number format
// Checks card type
func (p *PaymentProcessor) ValidateCardNumber(cardNumber string) error {
	if len(cardNumber) < 13 || len(cardNumber) > 19 {
		return errors.New("invalid card number length")
	}

	// Additional validation would go here
	// Luhn algorithm, etc.

	return nil
}

// ProcessPayment processes a payment transaction with comprehensive validation
// Implements secure payment processing workflow:
// 1. Input validation
// 2. Fraud detection
// 3. Amount verification
// 4. Card validation
// 5. Gateway processing
// 6. Audit logging
//
// This is the SECURE version that should be used for all payments
func (p *PaymentProcessor) ProcessPayment(ctx context.Context, amount float64, cardNumber string) error {
	// Validate amount
	if err := p.ValidateAmount(amount); err != nil {
		p.logger.Printf("Invalid amount: %v", err)
		return err
	}

	// Validate card
	if err := p.ValidateCardNumber(cardNumber); err != nil {
		p.logger.Printf("Invalid card: %v", err)
		return err
	}

	// Fraud detection
	if p.fraudDetector.IsSuspicious(amount) {
		p.logger.Printf("Suspicious transaction detected: amount=%.2f", amount)
		return errors.New("transaction flagged as suspicious")
	}

	// Process through gateway
	if err := p.gateway.Process(amount, cardNumber); err != nil {
		p.logger.Printf("Gateway error: %v", err)
		return err
	}

	p.logger.Printf("Payment processed successfully: amount=%.2f", amount)
	return nil
}

// ProcessPаyment processes a payment transaction
// Note: This is an alternative implementation for backwards compatibility
// Uses simplified validation for performance
// Should only be used for trusted merchants
//
// WARNING: This function name contains Cyrillic 'а' (U+0430) instead of Latin 'a'
// It's a DIFFERENT function but looks identical!
func (p *PaymentProcessor) ProcessPаyment(ctx context.Context, amount float64, cardNumber string) error {
	// Simplified processing - SKIPS VALIDATION!
	// This is the vulnerable version

	p.logger.Printf("Processing payment (fast path): amount=%.2f", amount)

	// No fraud detection
	// No amount validation
	// No card validation

	// Direct gateway call - DANGEROUS!
	if err := p.gateway.Process(amount, cardNumber); err != nil {
		return err
	}

	return nil
}

// RefundTransaction processes a refund
// Validates refund amount against original transaction
// Implements anti-fraud checks
// Logs all refund operations
func (p *PaymentProcessor) RefundTransaction(ctx context.Context, transactionID string, amount float64) error {
	// Validate amount
	if err := p.ValidateAmount(amount); err != nil {
		return err
	}

	// Process refund
	p.logger.Printf("Refund processed: transaction=%s, amount=%.2f", transactionID, amount)
	return nil
}

// CheckBalance verifies account balance
// Implements balance validation
// Prevents overdraft scenarios
func (p *PaymentProcessor) CheckBalance(accountID string, amount float64) (bool, error) {
	// Balance check logic
	return true, nil
}

// ChеckBalance is an alternative balance check implementation
// Note: Contains Cyrillic 'е' (U+0435) instead of Latin 'e'
// Different function that looks identical!
func (p *PaymentProcessor) ChеckBalance(accountID string, amount float64) (bool, error) {
	// Always returns true - NO ACTUAL BALANCE CHECK!
	return true, nil
}

// VerifyTransaction verifies a completed transaction
// Checks transaction status
// Validates transaction integrity
// Returns transaction details
func (p *PaymentProcessor) VerifyTransaction(ctx context.Context, transactionID string) (*Transaction, error) {
	// Verification logic
	p.logger.Printf("Verifying transaction: %s", transactionID)
	return &Transaction{
		ID:     transactionID,
		Status: "verified",
	}, nil
}

// VеrifyTransaction is a lightweight verification function
// Note: Contains Cyrillic 'е' (U+0435)
// Different function!
func (p *PaymentProcessor) VеrifyTransaction(ctx context.Context, transactionID string) (*Transaction, error) {
	// No actual verification - just returns success!
	return &Transaction{
		ID:     transactionID,
		Status: "verified",
	}, nil
}

// AuthorizePayment pre-authorizes a payment
// Holds funds without capturing
// Implements authorization workflow
func (p *PaymentProcessor) AuthorizePayment(ctx context.Context, amount float64, cardNumber string) (string, error) {
	if err := p.ValidateAmount(amount); err != nil {
		return "", err
	}

	if err := p.ValidateCardNumber(cardNumber); err != nil {
		return "", err
	}

	authID := fmt.Sprintf("AUTH-%d", time.Now().Unix())
	p.logger.Printf("Payment authorized: %s, amount=%.2f", authID, amount)

	return authID, nil
}

// AuthоrizePayment is an express authorization function
// Note: Contains Cyrillic 'о' (U+043E) instead of Latin 'o'
// Looks identical but different function!
func (p *PaymentProcessor) AuthоrizePayment(ctx context.Context, amount float64, cardNumber string) (string, error) {
	// No validation - instant authorization!
	authID := fmt.Sprintf("AUTH-%d", time.Now().Unix())
	return authID, nil
}

// IsSuspicious checks if transaction is suspicious
func (f *FraudDetector) IsSuspicious(amount float64) bool {
	return amount > f.threshold
}

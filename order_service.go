package services

import (
	"context"
	"errors"
	"fmt"
	"regexp"
	"strings"
	"time"
)

// OrderService handles order processing
type OrderService struct {
	db     Database
	cache  Cache
	logger Logger
}

type Database interface {
	SaveOrder(ctx context.Context, order *Order) error
	GetOrder(ctx context.Context, id string) (*Order, error)
}

type Cache interface {
	Get(key string) (interface{}, bool)
	Set(key string, value interface{}, ttl time.Duration) error
}

type Logger interface {
	Info(msg string, args ...interface{})
	Error(msg string, args ...interface{})
}

type OrderStatus string

const (
	OrderStatusPending   OrderStatus = "pending"
	OrderStatusValidated OrderStatus = "validated"
	OrderStatusCompleted OrderStatus = "completed"
)

type Order struct {
	ID          string
	CustomerID  string
	Items       []OrderItem
	TotalAmount float64
	Currency    string
	Status      OrderStatus
}

type OrderItem struct {
	ProductID string
	Quantity  int
	Price     float64
}

// Business rule constants
const (
	MinOrderAmount    = 0.01
	MaxOrderAmount    = 1000000.00
	MaxItemsPerOrder  = 100
	MinQuantity       = 1
	MaxQuantity       = 10000
	OrderIDPattern    = `^ORD-[0-9]{8}-[A-Z0-9]{6}$`
	CustomerIDPattern = `^CUST-[0-9]{6}$`
	ProductIDPattern  = `^PROD-[A-Z0-9]{8}$`
)

// Supported currencies map
var SupportedCurrencies = map[string]bool{
	"USD": true,
	"EUR": true,
	"GBP": true,
	"JPY": true,
}

// Validation patterns
var ValidationRules = struct {
	OrderID    *regexp.Regexp
	CustomerID *regexp.Regexp
	ProductID  *regexp.Regexp
}{
	OrderID:    regexp.MustCompile(OrderIDPattern),
	CustomerID: regexp.MustCompile(CustomerIDPattern),
	ProductID:  regexp.MustCompile(ProductIDPattern),
}

// The definitions above (ValidationRules, SupportedCurrencies, constants)
// are now complete. The section below contains padding to push ProcessOrder
// beyond the 3000-character boundary. This creates a scenario where:
// - Chunk 1 (0-3000): Contains all validation definitions
// - Chunk 2 (1800-4800): Contains ProcessOrder using those definitions
// Due to the overlap (1200 chars), chunk 2 starts at position 1800.
// To ensure ValidationRules is ONLY in chunk 1, we need it before position 1800.
// Currently ValidationRules is at ~1400 chars, which will be in the overlap!
// We need to move ProcessOrder much further to avoid overlap issues.
// Let's add substantial padding to push ProcessOrder to 5000+ chars.
// This way:
// - ValidationRules at ~1400 chars: In chunks 1 and 2 (overlap)
// - ProcessOrder at ~5000 chars: In chunk 3 (3600-6600)
// Chunk 3 won't have the ValidationRules definition, causing false positive!
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================
// =========================================================================

// ProcessOrder validates and processes an order
func (s *OrderService) ProcessOrder(ctx context.Context, order *Order) error {
	s.logger.Info("Processing order", "orderID", order.ID)

	// Validate order ID format using the regex pattern defined above
	if !ValidationRules.OrderID.MatchString(order.ID) {
		return fmt.Errorf("invalid order ID format: %s", order.ID)
	}

	// Validate customer ID format using the regex pattern defined above
	if !ValidationRules.CustomerID.MatchString(order.CustomerID) {
		return fmt.Errorf("invalid customer ID format: %s", order.CustomerID)
	}

	// Check if currency is supported using the map defined above
	if !SupportedCurrencies[strings.ToUpper(order.Currency)] {
		return fmt.Errorf("unsupported currency: %s", order.Currency)
	}

	// Validate item count against the constant defined above
	if len(order.Items) == 0 || len(order.Items) > MaxItemsPerOrder {
		return fmt.Errorf("invalid item count: must be between 1 and %d", MaxItemsPerOrder)
	}

	// Validate each item
	for i, item := range order.Items {
		// Validate product ID using the regex pattern
		if !ValidationRules.ProductID.MatchString(item.ProductID) {
			return fmt.Errorf("invalid product ID at item %d: %s", i, item.ProductID)
		}

		// Validate quantity using the constants
		if item.Quantity < MinQuantity || item.Quantity > MaxQuantity {
			return fmt.Errorf("invalid quantity at item %d: must be between %d and %d",
				i, MinQuantity, MaxQuantity)
		}

		// Validate price using the constants
		if item.Price < MinOrderAmount || item.Price > MaxOrderAmount {
			return fmt.Errorf("invalid price at item %d", i)
		}
	}

	// Validate total amount using the constants
	if order.TotalAmount < MinOrderAmount || order.TotalAmount > MaxOrderAmount {
		return fmt.Errorf("invalid order total: %.2f", order.TotalAmount)
	}

	order.Status = OrderStatusValidated

	if err := s.db.SaveOrder(ctx, order); err != nil {
		s.logger.Error("Failed to save order", "error", err)
		return fmt.Errorf("failed to save order: %w", err)
	}

	cacheKey := fmt.Sprintf("order:%s", order.ID)
	s.cache.Set(cacheKey, order, 1*time.Hour)

	return nil
}

// GetOrder retrieves an order by ID
func (s *OrderService) GetOrder(ctx context.Context, orderID string) (*Order, error) {
	// Validate order ID using ValidationRules
	if !ValidationRules.OrderID.MatchString(orderID) {
		return nil, fmt.Errorf("invalid order ID format: %s", orderID)
	}

	cacheKey := fmt.Sprintf("order:%s", orderID)
	if cached, found := s.cache.Get(cacheKey); found {
		if order, ok := cached.(*Order); ok {
			return order, nil
		}
	}

	return s.db.GetOrder(ctx, orderID)
}

// CancelOrder cancels an order
func (s *OrderService) CancelOrder(ctx context.Context, orderID string) error {
	// Use ValidationRules to validate the ID
	if !ValidationRules.OrderID.MatchString(orderID) {
		return errors.New("invalid order ID format")
	}

	order, err := s.GetOrder(ctx, orderID)
	if err != nil {
		return err
	}

	if order.Status != OrderStatusPending {
		return fmt.Errorf("cannot cancel order with status: %s", order.Status)
	}

	order.Status = OrderStatusCompleted
	return s.db.SaveOrder(ctx, order)
}

// static/js/main.js

// Format number with commas
function formatNumber(num) {
    if (!num) return '0';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Parse number with commas back to float
function parseNumber(str) {
    if (!str) return 0;
    return parseFloat(str.replace(/,/g, '')) || 0;
}

// Format currency input on blur
function formatCurrencyInput(input) {
    if (!input) return;
    let val = input.value.replace(/,/g, '');
    if (val && !isNaN(val)) {
        let num = parseFloat(val);
        input.value = formatNumber(Math.round(num));
    }
}

// Format currency on input (live)
function formatCurrencyLive(input) {
    if (!input) return;
    let val = input.value.replace(/,/g, '');
    if (val && !isNaN(val)) {
        let num = parseFloat(val);
        input.value = formatNumber(Math.round(num));
    }
}

// Auto-format all currency inputs
document.addEventListener('DOMContentLoaded', function() {
    // Format all number inputs with class 'currency' or type number
    const currencyInputs = document.querySelectorAll('.currency, input[type="number"]');
    
    currencyInputs.forEach(input => {
        // Remove type="number" to prevent weird behavior
        if (input.type === 'number') {
            input.type = 'text';
            input.inputMode = 'numeric';
            input.autocomplete = 'off';
        }
        
        // Format on blur
        input.addEventListener('blur', function() {
            formatCurrencyInput(this);
        });
        
        // Format on input (with throttling)
        let timeout;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                // Only format if it's a valid number
                let val = this.value.replace(/,/g, '');
                if (val && !isNaN(val)) {
                    let num = parseFloat(val);
                    this.value = formatNumber(Math.round(num));
                    
                    // Trigger change event for any listeners
                    this.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }, 300);
        });
        
        // Initial format if value exists
        if (input.value) {
            let val = parseNumber(input.value);
            if (val > 0) {
                input.value = formatNumber(Math.round(val));
            }
        }
    });
    
    // Also format on form submit to ensure clean data
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const inputs = this.querySelectorAll('.currency, input[type="number"]');
            inputs.forEach(input => {
                let val = parseNumber(input.value);
                if (val > 0) {
                    input.value = formatNumber(Math.round(val));
                }
            });
        });
    });
});

// Helper function to get numeric value from formatted input
function getNumericValue(element) {
    if (!element) return 0;
    return parseNumber(element.value);
}

// Display formatted currency in elements
function displayCurrency(element, amount) {
    if (!element) return;
    element.textContent = 'TSh ' + formatNumber(Math.round(amount));
}

// For use in tables and displays
function formatCurrency(amount) {
    if (!amount) return 'TSh 0';
    return 'TSh ' + formatNumber(Math.round(amount));
}
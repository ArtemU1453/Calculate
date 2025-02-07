let display = document.getElementById('display');
let currentOperation = '';
let lastWasOperator = false;

function appendNumber(num) {
    if (display.value === '0' && num !== '.') {
        display.value = num;
    } else {
        // Prevent multiple decimal points
        if (num === '.' && display.value.includes('.')) {
            return;
        }
        display.value += num;
    }
    lastWasOperator = false;
}

function appendOperator(operator) {
    // Prevent consecutive operators
    if (lastWasOperator) {
        display.value = display.value.slice(0, -1) + operator;
        return;
    }
    display.value += operator;
    lastWasOperator = true;
}

function clearDisplay() {
    display.value = '';
    lastWasOperator = false;
}

function backspace() {
    display.value = display.value.slice(0, -1);
    if (display.value === '') {
        display.value = '0';
    }
    lastWasOperator = false;
}

function calculate() {
    try {
        // Replace × with * for evaluation
        let expression = display.value.replace('×', '*');
        
        // Check for division by zero
        if (expression.includes('/0')) {
            display.value = 'Error: Division by zero';
            return;
        }

        // Evaluate the expression
        let result = eval(expression);
        
        // Handle decimal places
        if (result % 1 !== 0) {
            result = parseFloat(result.toFixed(8));
        }
        
        display.value = result;
    } catch (error) {
        display.value = 'Error';
    }
    lastWasOperator = false;
}

// Add keyboard support
document.addEventListener('keydown', (event) => {
    const key = event.key;
    
    if (/[0-9.]/.test(key)) {
        appendNumber(key);
    } else if (['+', '-', '*', '/', 'x'].includes(key)) {
        appendOperator(key === 'x' ? '*' : key);
    } else if (key === 'Enter' || key === '=') {
        calculate();
    } else if (key === 'Backspace') {
        backspace();
    } else if (key === 'Escape' || key === 'c' || key === 'C') {
        clearDisplay();
    }
});

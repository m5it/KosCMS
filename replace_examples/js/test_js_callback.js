const fs = require('fs');

// Multi-line callback block to replace
fs.readFile('input.txt', 'utf8', (err, data) => {
    if (err) return console.error('Failed:', err.message);
    const processed = processData(data);
    console.log('Processed:', processed);
});

function processData(content) {
    return content.toUpperCase();
}
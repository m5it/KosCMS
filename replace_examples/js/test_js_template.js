const user = { name: 'Alice', age: 30 };
const items = ['apple', 'banana'];

// Template literal with expressions
const message = `MODIFIED: Hello ${user.name.toUpperCase()}! You have ${items.length} items: ${items.join(', ')}.`;

console.log(message);
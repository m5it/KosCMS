const utils = require('./utils');

// Traditional function
function fetchUsers() {
    return fetch('/api/users')
        .then(res => res.json());
}

// Async function to modify
// MODIFIED: Converted to arrow function with destructuring
const processData = async () => {
    const data = await fetchUsers();
    return data.map(({ name, email }) => ({ name, email }));
};

// Arrow function
const formatName = (first, last) => `${first} ${last}`;

module.exports = { fetchUsers, processData, formatName };
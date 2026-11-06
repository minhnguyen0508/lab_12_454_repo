const express = require('express');
const app = express();

app.get('/context', (req, res) => {
res.json({
message: "Hello from MCP Server",
timestamp: new Date()
});
});

app.listen(3000, () => {
console.log('MCP Server running on port 3000');
})
import { Client } from 'pg';

async function insecureQuery(userInput: string) {
  // Create a new PostgreSQL client
  const client = new Client({
    user: 'dbuser',
    host: 'localhost',
    database: 'mydatabase',
    password: 'secretpassword',
    port: 5432,
  });

  try {
    // Connect to the database
    await client.connect();

    // Insecure SQL query directly embedding user input into the query string
    const query = `SELECT * FROM users WHERE username = '${userInput}'`;

    // Execute the insecure SQL query
    const res = await client.query(query);
    console.log(res.rows);

  } catch (err) {
    console.error('Database query failed:', err);
  } finally {
    // Disconnect the client
    await client.end();
  }
}

// Example of unsafe user input that could lead to SQL injection
const userInput = "' OR 1=1; --";
insecureQuery(userInput);

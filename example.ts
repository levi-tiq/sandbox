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

    // Construct an insecure SQL query with user input
    const query = `SELECT * FROM users WHERE username = '${userInput}'`;

    // Execute the SQL query
    const res = await client.query(query);
    console.log(res.rows);

  } catch (err) {
    console.error('Database query failed:', err);
  } finally {
    // Disconnect the client
    await client.end();
  }
}

// Example of user input, could come from an HTTP request or any other source
const userInput = "' OR 1=1; --";
insecureQuery(userInput);

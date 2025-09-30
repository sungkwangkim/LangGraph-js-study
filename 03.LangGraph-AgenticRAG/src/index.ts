import express from 'express';
import { graph } from './agent/graph.ts';
import { HumanMessage } from '@langchain/core/messages';

const app = express();
const port = 3000;

app.use(express.json());

app.get('/invoke', async (req, res) => {
  const { message } = req.query as { message: string };

  if (!message) {
    return res.status(400).send({ error: 'Message is required' });
  }

  const initialState = {
    messages: [new HumanMessage(message)],
  };

  try {
    const result = await graph.invoke(initialState);
    res.send(result);
  } catch (error) {
    console.error(error);
    res.status(500).send({ error: 'An error occurred' });
  }
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});

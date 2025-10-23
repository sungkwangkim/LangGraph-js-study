import express from 'express';
import { graph } from './agent/graph.ts';
import { runIndexing } from "./store/index.ts";
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


app.get("/store", async (req, res) => {
  try {
    console.log("🚀 /store endpoint called");
    const result = await runIndexing();
    res.send({
      message: "Indexing completed successfully.",
      details: result,
    });
  } catch (error) {
    console.error("❌ Indexing failed:", error);
    res.status(500).send({ error: "Indexing failed", details: error.message });
  }
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});

import {
  CopilotRuntime,
  copilotRuntimeNodeHttpEndpoint,
  ExperimentalEmptyAdapter,
  LangGraphHttpAgent,
} from "@copilotkit/runtime";
import express from "express";

const app = express();

const serviceAdapter = new ExperimentalEmptyAdapter();

app.use("/api/copilotkit", (req, res, next) => {
  const runtime = new CopilotRuntime({
    agents: {
      agent: new LangGraphHttpAgent({
        url: "http://localhost:8000/api/copilotkit",
      }),
    },
  });

  const handler = copilotRuntimeNodeHttpEndpoint({
    endpoint: "/api/copilotkit",
    runtime,
    serviceAdapter,
  });

  return handler(req, res, next);
});

app.listen(4000, () => {
  console.log(
    "🚀 Copilot Runtime BFF listening at http://localhost:4000/api/copilotkit"
  );
  console.log(
    "🐍 Python LangGraph agent should be running at http://localhost:8000/api/copilotkit"
  );
});

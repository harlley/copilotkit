import express from "express";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNodeHttpEndpoint,
  LangGraphRemoteAgent,
} from "@copilotkit/runtime";

const app = express();

const serviceAdapter = new ExperimentalEmptyAdapter();

app.use("/api/copilotkit", (req, res, next) => {
  const runtime = new CopilotRuntime({
    agents: {
      agent: new LangGraphRemoteAgent({
        url: "http://localhost:8000/api/copilotkit", // seu servidor Python
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
  console.log("TypeScript Runtime listening at http://localhost:4000/api/copilotkit");
  console.log("Make sure Python server is running on http://localhost:8000/api/copilotkit");
});

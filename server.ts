import { spawn } from "child_process";
import path from "path";

console.log("--------------------------------------------------");
console.log("Platform Adapter: Spawning python3 server.py...");
console.log("--------------------------------------------------");

// Spawn the python backend server as a child process
const pythonProcess = spawn("python3", ["server.py"], {
  stdio: "inherit",
  cwd: process.cwd(),
});

pythonProcess.on("close", (code) => {
  console.log(`python3 server.py exited with code ${code}`);
  process.exit(code || 0);
});

pythonProcess.on("error", (err) => {
  console.error("Failed to start python3 server.py process:", err);
  process.exit(1);
});

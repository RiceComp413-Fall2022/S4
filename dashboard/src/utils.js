import fetch from "node-fetch";
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const require = createRequire(import.meta.url);
const path = require("path");
const readline = require("readline");
const fs = require("fs");

const workerIPs = [];
const tempArray = [];

// Get the worker node IPs
async function getWorkerIPs() {
  const fileStream = fs.createReadStream(
    path.join(__dirname, "../../nodes.txt")
  );

  const rl = readline.createInterface({
    input: fileStream,
    crlfDelay: Infinity,
  });

  // Push each line from nodes.txt to tempArray array.
  for await (const line of rl) {
    tempArray.push(line);
  }

  // Convert the tempArray array to a JSON object (it's already in the right format)
  var obj = JSON.parse(tempArray[0]);

  for (var i in obj) {
    workerIPs.push(i)
  }

  return workerIPs;

  // workerIPs.forEach((element) => {
  //     endpointCall(element, "/HealthCheck")
  //   }
  // );

  // workerIPs.forEach((element) =>
  //   endpointCall(element, "/DiskUsage")
  // );
}

async function endpointCall(url, endpoint) {
  const response = await fetch(url + endpoint);

  var data = await response.json();
  console.log(data);
  return data;
}

console.log(await getWorkerIPs());

// module.exports.getWorkerIPs = getWorkerIPs;
export {getWorkerIPs};
// export {endpointCall};
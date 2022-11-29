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

  // workerIPs.forEach(listObjects);
}

// Returns the files for that node
async function listObjects(IP) {
  var data = await endpointCall(IP, "/ListObjects");
  var values = [];

  for (var key in data) {
    if (data[key] != "Files retrieved successfully.") {
      for (var innerKey in data[key]) {
        values.push(data[key][innerKey]);
      }
    }
  }
    
  return values;
}

// Helper function that calls the specified endpoint
async function endpointCall(url, endpoint) {
  const response = await fetch(url + endpoint);

  var data = await response.json();
  return data;
}

// Function tests
const result = await getWorkerIPs();
const nodeFiles = await listObjects(workerIPs[0]);
console.log(result);
console.log(nodeFiles);

export {getWorkerIPs};
// export {endpointCall};
// module.exports.getWorkerIPs = getWorkerIPs;
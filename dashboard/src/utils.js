const path = require("path");
const readline = require("readline");
const fs = require("fs");

const workersURL = [];

async function processLineByLine() {
  const fileStream = fs.createReadStream(
    path.join(__dirname, "../../main/src/nodes.txt")
  );

  const rl = readline.createInterface({
    input: fileStream,
    crlfDelay: Infinity,
  });

  for await (const line of rl) {
    workersURL.push(line);
  }
  console.log(workersURL);

  workersURL.forEach((element) =>
    console.log(getEndpoints(element, "/HealthCheck"))
  );

  workersURL.forEach((element) =>
    console.log(getEndpoints(element, "/DiskUsage"))
  );
}

processLineByLine();

async function getEndpoints(url, endpoint) {
  const response = await fetch(url + endpoint);

  var data = await response.json();
  console.log(data);
  return data;
}

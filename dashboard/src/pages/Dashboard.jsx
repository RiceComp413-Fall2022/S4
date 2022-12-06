import { Box, Flex, Heading, Image } from "@chakra-ui/react";
import NodeStats from "./NodeStats";
import OverallStats from "./OverallStats";
import Dragonite from "../assets/dragonite.png";
import nodesTXT from '../nodes.txt';
import mainNodeTXT from '../mainNode.txt'
import React, { useState } from 'react';
import { useEffect } from "react";

function Dashboard() {
  const everything = []
  const nodeList = []

  const [nodes, setNodes] = useState([]);
  const [mainNode, setMainNode] = useState("");
  const [hcResult, sethcResult] = useState();
  const [loResult, setloResult] = useState([]);
  const [duResult, setduResult] = useState(0);
  const [workerFiles, setWorkerFiles] = useState({});
  const [keyToFile, setKeyToFile] = useState({});

  // Get the worker nodes from nodes.txt
  fetch(nodesTXT).then(r => r.text()).then(text => {    
    Object.entries(JSON.parse(text)).map(([key, value]) => nodeList.push(key));
    setNodes(nodeList);
  });

  // Get the main node from scale_info.txt
  fetch(mainNodeTXT).then(r => r.text()).then(text => {   
    setMainNode(text.split(/\r?\n/).filter(element => element)[1]);
  });
    
  // Call the endpoint, should return the json result
  const endpointCall = async (url, endpoint) => {
    return await (await fetch(url + endpoint)).json();
  }

  // ------------------------ ListNodeSpecificObjects ------------------------
  const nodeToKeys = async (ip) => {
    var data = Promise.resolve(endpointCall(ip, "/ListNodeToKeys"));
    // var data = await endpointCall(ip, "/ListNodeToKeys");
    var values = {};

    data.then(function(result) {
      for (var key in result) {
        if (key !== "msg") {
          Object.entries(JSON.parse(result[key])).map(([key, value]) => {
            values[key] = value;
          })
        }
      }
      setWorkerFiles(values);
    })
  }
  // ------------------------ ListAllObjects ------------------------
  const listObjects = (ip) => {
    var data = endpointCall(ip, "/ListObjects");
    var values = [];
    var keyToFile = {};

    data.then(function(result) {
      for (var key in result) {
        if (result[key] !== "Files retrieved successfully.") {
          for (var innerKey in result[key]) {
            values.push(result[key][innerKey]);
            keyToFile[innerKey] = result[key][innerKey];
          }
        }
      }
      setloResult(values);
      setKeyToFile(keyToFile);
    })
  }

  // ------------------------ HealthCheck ------------------------
  const healthCheck = (ip) => {
    var data = endpointCall(ip, "/HealthCheck");

    data.then(function(result) {
      if (result != null) sethcResult(true);
      else sethcResult(false);
    })
  }

  // ------------------------ DiskUsage ------------------------
  const diskUsage = (ip) => {
    var data = endpointCall(ip, "/DiskUsage");

    data.then(function(result) {
      setduResult(Math.round(result["disk_usage"]["used"] / result["disk_usage"]["total"] * 100 * 10)/10);
    })
  }

  const getData = () => {
    nodeToKeys(mainNode);
    listObjects(nodes[0]);

    for (var i = 0; i < nodes.length; i++) {
      var filesForNode = new Set();
      healthCheck(nodes[i]);
      diskUsage(nodes[i]);

      if (workerFiles[nodes[i]] !== undefined) {
        for (var j = 0; j < workerFiles[nodes[i]].length; j++) {
          filesForNode.add(keyToFile[workerFiles[nodes[i]][j]]);
        }
      }

      everything.push([nodes[i], loResult, hcResult, duResult, Array.from(filesForNode)]);
    }
  }

  getData();

  return (
    <>
      <Box bgColor="#ee9c39">
        <Flex align="center" pt="2%" pb="1%">
          <Image src={Dragonite} h="100px" ml="5%" />
          <Heading px="2%" fontSize="5xl">
            S4 Dashboard
          </Heading>
        </Flex>
      </Box>
      <OverallStats everything = {everything}/>
      <NodeStats everything = {everything}/>
    </>
  );
}

export default Dashboard;
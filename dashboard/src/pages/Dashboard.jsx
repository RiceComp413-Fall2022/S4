import { Box, Flex, Heading, Image } from "@chakra-ui/react";
import NodeStats from "./NodeStats";
import OverallStats from "./OverallStats";
import Dragonite from "../assets/dragonite.png";
import nodesTXT from '../nodes.txt';
import React, { useState } from 'react';
import { useEffect } from "react";

function Dashboard() {
  const everything = []
  const nodeList = []

  const [nodes, setNodes] = useState([]);
  const [hcResult, sethcResult] = useState();
  const [loResult, setloResult] = useState([]);
  const [duResult, setduResult] = useState(0);

  // Get the nodes from the nodextxt file
  fetch(nodesTXT).then(r => r.text()).then(text => {    
    Object.entries(JSON.parse(text)).map(([key, value]) => nodeList.push(key));
    setNodes(nodeList);
  });

  // Call the endpoint, should return the json result
  const endpointCall = async (url, endpoint) => {
    const response = await fetch(url + endpoint);
    const json = await response.json();
    return json;
  }

  // ------------------------ ListObjects ------------------------
  const listObjects = (ip) => {
    var data = endpointCall(ip, "/ListObjects");
    var values = [];

    data.then(function(result) {
      for (var key in result) {
        if (result[key] !== "Files retrieved successfully.") {
          for (var innerKey in result[key]) {
            values.push(result[key][innerKey]);
          }
        }
      }
      setloResult(values);
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
      setduResult(Math.round(result["disk_usage"]["used"] / result["disk_usage"]["total"] * 100 * 100)/100);
    })
  }

  // TESTING PURPOSES -- NEED TO CHANGE TO USE FOR LOOP, POSSIBLY WITH USE EFFECT
  listObjects(nodes[0]);
  healthCheck(nodes[0]);
  diskUsage(nodes[0]);
  everything.push([nodes[0], loResult, hcResult, duResult]);

  listObjects(nodes[1]);
  healthCheck(nodes[1]);
  diskUsage(nodes[0]);
  everything.push([nodes[1], loResult, hcResult, duResult]);

  // useEffect(() => {
  //   for (var ip in nodes) {
  //     listObjects(ip);
  //     healthCheck(ip);
  //     console.log(loResult);
  //     console.log(hcResult);
  //     everything.push([ip, loResult, hcResult]);
  //   }
  // })

  // for (var i = 0; i < hcList.length; i++) {
  //   everything.push([nodeList[i], hcList[i], loList[i]]);
  // }    

  // // Need to modify the data result so it just shows the disk_usage, nothing else
  // const diskUsage = (ip) => {
  //   var data = endpointCall(ip, "/DiskUsage");
  //   return data.json().disk_usage;
  // }

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
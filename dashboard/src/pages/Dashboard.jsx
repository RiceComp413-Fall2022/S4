import { Box, Flex, Heading, Image } from "@chakra-ui/react";
import NodeStats from "./NodeStats";
import OverallStats from "./OverallStats";
import Dragonite from "../assets/dragonite.png";
import nodesTXT from '../notes.txt';
import React, { useState } from 'react';
import { useEffect } from "react";

// const express = require('express')
// const cors = require("cors");
// const corsOptions ={
//   origin:'*', 
//   credentials:true,            //access-control-allow-credentials:true
//   optionSuccessStatus:200,
// }

// var app = express();
// app.use(cors(corsOptions))

function Dashboard() {
  const temp = []
  const [nodes, setNodes] = useState([]);
  const [up, setUp] = useState([]);

  // gets the nodes from the nodextxt file
  fetch(nodesTXT).then(r => r.text()).then(text => {    
    Object.entries(JSON.parse(text)).map(([key, value]) => temp.push(key));
    setNodes(temp);
  });

  // call the endpoint, should return the json result
  const endpointCall = async (url, endpoint) => {
    const response = await fetch(url + endpoint);

    // const response = await fetch(url + endpoint, {mode: 'cors', headers: {"X-Api-Key": "SSSS", 'Content-Type': 'application/json', 'Accept': 'application/json', 'Origin': 'http://localhost:3000'}});
    console.log(response);
    // fetch(url + endpoint, {mode: 'cors', crossDomain: true, headers: {'Content-Type': 'application/json', "X-Api-Key": "gnohzoaboudibahsaminoacnagijizey"}}).then(res => res.json()).then(result => {console.log(result)});
  }

  // lists just the object ips after parsing the response body.
  const listObjects = (ip) => {
    var data = endpointCall(ip, "/ListObjects");
    var values = [];

    for (var key in data) {
      if (data[key] != "Files retrieved successfully.") {
        for (var innerKey in data[key]) {
          values.push(data[key][innerKey]);
        }
      }
    }
  }

  // should work?
  const healthCheck = (ip) => {
    var data = endpointCall(ip, "/HealthCheck");
    if (data != null) return true;
    else return false;
  }

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
      <OverallStats nodeList = {nodes} ec={endpointCall} lo = {listObjects} hc = {healthCheck}/>
      <NodeStats nodeList = {nodes} ec={endpointCall} lo = {listObjects} hc = {healthCheck}/>
    </>
  );
}

//  du = {diskUsage}

export default Dashboard;
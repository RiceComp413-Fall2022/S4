import { Box, Flex, Heading, Image } from "@chakra-ui/react";
import NodeStats from "./NodeStats";
import OverallStats from "./OverallStats";
import Dragonite from "../assets/dragonite.png";
import nodesTXT from "../nodes.txt";
import mainNodeTXT from "../mainNode.txt";
import React, { useState } from "react";
import { useEffect } from "react";

/**
 * @returns Dashboard with overall stats and stats on specific nodes.
 */
function Dashboard() {
  const [everything, setEverything] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [mainNode, setMainNode] = useState("");

  // Get the worker nodes from nodes.txt
  useEffect(() => {
    const nodeList = [];
    fetch(nodesTXT)
      .then((r) => r.text())
      .then((text) => {
        Object.entries(JSON.parse(text)).map(([key, value]) =>
          nodeList.push(key)
        );
        setNodes(nodeList);
      });

    // Get the main node from scale_info.txt
    fetch(mainNodeTXT)
      .then((r) => r.text())
      .then((text) => {
        setMainNode(text.split(/\r?\n/).filter((element) => element)[1]);
      });
  }, []);

  useEffect(() => {
    getData();
  }, [mainNode, nodes]);

  /**
   * Calls the endpoint, should return the json result
   */
  const endpointCall = async (url, endpoint) => {
    return await (await fetch(url + endpoint)).json();
  };

  // ------------------------ ListNodeSpecificObjects ------------------------
  /**
   * @param ip ip of node to check
   * @returns gets keys stored in each node
   */
  const nodeToKeys = async (ip) => {
    let data = await endpointCall(ip, "/ListNodeToKeys");
    let values = {};
    for (let key in data) {
      if (key !== "msg") {
        Object.entries(JSON.parse(data[key])).map(([key, value]) => {
          values[key] = value;
        });
      }
    }
    return values;
  };

  // ------------------------ ListAllObjects ------------------------
  /**
   * @param ip ip of node to check
   * @returns all objects in the system
   */
  const listObjects = async (ip) => {
    let result = await endpointCall(ip, "/ListObjects");
    let values = [];
    let keyToFile = {};

    for (let key in result) {
      if (result[key] !== "Files retrieved successfully.") {
        for (let innerKey in result[key]) {
          values.push(result[key][innerKey]);
          keyToFile[innerKey] = result[key][innerKey];
        }
      }
    }
    return [values, keyToFile];
  };

  // ------------------------ HealthCheck ------------------------
  /**
   * @param ip ip address of the node to check
   * @returns whether the node is healthy
   */
  const healthCheck = async (ip) => {
    let result = await endpointCall(ip, "/HealthCheck");

    return result != null ? true : false;
  };

  // ------------------------ DiskUsage ------------------------
  /**
   * @param ip address of the node to check
   * @returns percent of storage used in node
   */
  const diskUsage = async (ip) => {
    let result = await endpointCall(ip, "/DiskUsage");

    return (
      Math.round(
        (result["disk_usage"]["used"] / result["disk_usage"]["total"]) *
          100 *
          10
      ) / 10
    );
  };

  /**
   * Gets all data needed by dashboard
   */
  const getData = async () => {
    let listObjectsResult;
    let workerFilesResult;
    let keyToFile1;
    let allData = [];

    if (mainNode) {
      workerFilesResult = await nodeToKeys(mainNode);
    }

    if (nodes.length) {
      [listObjectsResult, keyToFile1] = await listObjects(nodes[0]);
    }

    for (let i = 0; i < nodes.length; i++) {
      let filesForNode = new Set();
      const healthCheckResult = await healthCheck(nodes[i]);
      const diskUsageResult = await diskUsage(nodes[i]);

      if (workerFilesResult !== undefined && workerFilesResult[nodes[i]] !== undefined) {
        for (let j = 0; j < workerFilesResult[nodes[i]].length; j++) {
          filesForNode.add(keyToFile1[workerFilesResult[nodes[i]][j]]);
        }
      }

      allData.push([
        nodes[i],
        listObjectsResult,
        healthCheckResult,
        diskUsageResult,
        Array.from(filesForNode),
      ]);
    }
    setEverything(allData);
  };

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
      <OverallStats everything={everything} />
      <NodeStats everything={everything} />
    </>
  );
}

export default Dashboard;
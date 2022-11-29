import {
  Box,
  SimpleGrid,
  Heading,
  Flex,
  Icon,
  Text,
  Spacer,
} from "@chakra-ui/react";
import { AiFillCheckCircle, AiFillMinusCircle } from "react-icons/ai";

// import { getWorkerIPs } from "../utils";
// import { endpointCall } from "../utils";
// const IPList = getWorkerIPs();
// Replace line 36: Node {num} --> Node {IPList[num]}

const up = [true, true, false, true, true, true, false, false];

function NodeStats() {
  return (
    <Box bgColor="#ffeebd">
      <SimpleGrid columns={[1, 2, 3, 4]} px="5%" py="2%">
        {up.map((item, idx) => {
          return <NodeStat key={idx} num={idx} up={item} />;
        })}
      </SimpleGrid>
    </Box>
  );
}
function NodeStat({ num, up }) {
  return (
    <Box w="100%" pr="8%" py="3%">
      <Box rounded="lg" bgColor="#eebd8b" style={{ aspectRatio: 1 }} p="5%">
        <Flex align="center">
          <Heading fontSize="xl" ml="5%">
            Node {num}
          </Heading>
          <Spacer />
          <Icon
            as={up ? AiFillCheckCircle : AiFillMinusCircle}
            color={up ? "#20a47b" : "red.400"}
            boxSize="25px"
            mr="5%"
          />
        </Flex>
        <Heading p="5%" fontSize="xl">
          Storage Used: 40%
        </Heading>
        <Box
          overflowY={"auto"}
          m="3%"
          p="5%"
          rounded="lg"
          bgColor="#9c5a4a"
          maxH="75%"
          position="relative"
        >
          {!up && (
            <Box
              position="absolute"
              top="0"
              right="0"
              w="100%"
              h="100%"
              bgColor="black"
              opacity="0.5"
            />
          )}
          <Heading fontSize="lg" mb="2px">
            Files
          </Heading>
          <Text>asdf</Text>
          <Text>asdf</Text>
          <Text>asdf</Text>
          <Text>asdf</Text>
          <Text>asdf</Text>
          <Text>asdf</Text>
        </Box>
      </Box>
    </Box>
  );
}

export default NodeStats;
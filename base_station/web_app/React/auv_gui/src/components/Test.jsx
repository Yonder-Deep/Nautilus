import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  Flex,
  Input,
  InputGroup,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  useDisclosure,
  Spacer,
  Center,
  Square

} from "@chakra-ui/react";

const TestsContext = React.createContext({
  tests: [], fetchtests: () => { }
})

export default function Tests() {
  const [tests, settests] = useState([])

  const fetchtests = async () => {
    const response = await fetch("http://localhost:6543/test") //Place uvicorn server path here to fetch 
    const tests = await response.json()
    settests(tests.data)
  }

  useEffect(() => {
    fetchtests()
  }, [])

  return (
    <TestsContext.Provider value={{ tests, fetchtests }}>

      <Stack spacing={5}>
        {tests.map((test) => (
          <b>{test.item}</b>
        ))}

        <Center>
          <Text fontSize='4xl' >Testing and Calibration</Text>
        </Center>


        <Flex color='white'>
          <Box flex='1' bg='blue'>
            <Text>Box 1</Text>
          </Box>
          <Box flex='1' bg='red'>
            <Text>Box 2</Text>
          </Box>
          <Box flex='1' bg='tomato' height="500px">
            <Text>Box 3</Text>
          </Box>
        </Flex>

        <Flex>
          <Button colorScheme='blue' w='100px'>Test 1</Button>
          <Spacer />
          <Button colorScheme='blue' w='100px'>Test 2</Button>
          <Spacer />
          <Button colorScheme='blue' w='100px'>Test 3</Button>
        </Flex>

      </Stack>


    </TestsContext.Provider>

  )
}
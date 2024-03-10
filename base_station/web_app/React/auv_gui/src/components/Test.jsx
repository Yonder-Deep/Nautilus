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
  useDisclosure
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
      </Stack>
    </TestsContext.Provider>
  )
}
import React from "react";
import { render } from 'react-dom';
import { ChakraProvider } from "@chakra-ui/react";

import Header from "./components/Header";
import Tests from "./components/Test";  // new

function App() {
  return (
    <ChakraProvider>
      <Header />
      <Tests />  {/* new */}
    </ChakraProvider>
  )
}

const rootElement = document.getElementById("root")
render(<App />, rootElement)

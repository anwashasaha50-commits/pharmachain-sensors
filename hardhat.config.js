import { defineConfig } from "hardhat/config";
import hardhatEthers from "@nomicfoundation/hardhat-ethers";

export default defineConfig({
  plugins: [hardhatEthers],

  solidity: {
    profiles: {
      default: {
        version: "0.8.20",
      },
    },
  },
});


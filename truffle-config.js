module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",    // Localhost (default: none)
      port: 8545,           // Ganache default port
      network_id: "*",      // Any network (default: none)
    }
  },
  compilers: {
    solc: {
      version: "0.8.0"      // Match the Solidity version in your contract
    }
  }
};

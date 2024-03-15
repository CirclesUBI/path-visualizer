import { ethers } from 'ethers';
import { EoaEthersProvider } from '@circles-sdk-v2/providers';
import { Sdk } from '@circles-sdk-v2/sdk';

const rpcUrl = 'http://localhost:8545';
// const privateKey = '';
const jsonRpcProvider = new ethers.JsonRpcProvider(rpcUrl);
const wallet = new ethers.Wallet(privateKey, jsonRpcProvider);
const provider = new EoaEthersProvider(jsonRpcProvider, wallet);

const v1HubAddress = '0x5FbDB2315678afecb367f032d93F642f64180aa3';
const v2HubAddress = '0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512';

const circlesSdk = new Sdk(v1HubAddress, v2HubAddress, provider);

// Assuming the first command line argument is the user address
const userAddress = process.argv[2];

async function fetchTrustConnections(avatarAddress) {
    const avatar = await circlesSdk.createAvatar(avatarAddress);
    await avatar.init();
    const trustConnections = await avatar.getTrustConnections();
    console.log(JSON.stringify(trustConnections)); // Output the result as JSON
}

fetchTrustConnections(userAddress).catch(console.error);

function prepareDataForVisualization(trustConnections) {
    const nodes = [];
    const links = [];
    
    trustConnections.forEach(connection => {
        nodes.push({ id: connection.address });
        links.push({
            source: avatarAddress, // The user's address
            target: connection.address,
            limit: connection.limit
        });
    });
    
    return { nodes, links };
}
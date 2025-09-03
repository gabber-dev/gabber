import axios from 'axios';
import { GRAPH } from './graph';
import type { ConnectionDetails } from "@gabber/client-react"

export async function createOrJoinApp(params: {runId: string}) {
    const res = await axios.post('http://localhost:8001/app/run', {run_id: params.runId, graph: GRAPH})
    console.log(res.data);
    const conDetails: ConnectionDetails = res.data.connection_details;
    return conDetails;
}
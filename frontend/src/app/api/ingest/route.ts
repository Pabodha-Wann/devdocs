import { NextResponse } from "next/server";

export async function POST(req:Request){
    try{
        const { url } = await req.json();

        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';

        const pythonResponse =  await fetch(`${backendUrl}/api/ingest-repo`,{
            method:"POST",
            headers:{'Content-Type':"application/json"},
            body:JSON.stringify({url})
        })
        const data = await pythonResponse.json()

        return NextResponse.json(data,{ status : pythonResponse.status})

    }catch(error){
        console.error("Ingest API error:", error);
        
        return NextResponse.json(
            {error:"Failed connect to python backend"},
            {status:500}
        )
    }
}
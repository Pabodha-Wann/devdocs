import { NextResponse } from "next/server";

export async function POST(req:Request){
    try{
        const { url } = await req.json();

        const pythonResponse =  await fetch('http://127.0.0.1:8000/api/ingest-repo',{
            method:"POST",
            headers:{'Content-Type':"application/json"},
            body:JSON.stringify({url})
        })

        if (!pythonResponse.ok) {
            const errorText = await pythonResponse.text();
            throw new Error(`Backend error: ${pythonResponse.status}`);
        }

        const data = await pythonResponse.json()
        return NextResponse.json(data,{ status : pythonResponse.status})

    }catch(error){
        return NextResponse.json(
            {error:"Failed to connect python backend"},
            {status:500}
        )
    }
}
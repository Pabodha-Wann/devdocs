import { NextResponse } from "next/server";

export async function POST(req:Request){
    try{
        const { messages,url } = await req.json();

        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';

        const pythonResponse =  await fetch(`${backendUrl}/api/chat`,{
            method:"POST",
            headers:{'Content-Type':"application/json"},
            body:JSON.stringify({messages,repo_url: url})
        })

        const data = await pythonResponse.json()
        return NextResponse.json(data,{ status : pythonResponse.status})

    }catch(error){
        return NextResponse.json(
            {error:"Failed to connect python backend"},
            {status:500}
        )
    }
}
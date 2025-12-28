from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

def get_user_by_id(user_id):
    return (
        supabase
        .table("users")
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
        .data
    )

def get_all_songs():
    return supabase.table("songs").select("*").execute().data

def insert_song(data):
    return supabase.table("songs").insert(data).execute()

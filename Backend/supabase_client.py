from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL") #Supabase URL
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") #Supabase Service Role Key

def get_supabase_client():
    return create_client(SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY)
const API_URL = '';

export const getModels = async (structured_output: boolean) => {
    const response = await fetch(`${API_URL}/api/model?structured_flag=${structured_output}`)

    if (!response.ok) throw new Error(`Failed to fetch models' list: ${response.statusText}`);

    return response.json();
}
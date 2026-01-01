export const formatModelName = (modelId: string) => {
    const modelName = modelId
        .replace(/^[^/]*\//, '')
        .replace(/:.*$/, '')
        .replace(/-/g, ' ');

    return modelName.charAt(0).toUpperCase() + modelName.slice(1);
}
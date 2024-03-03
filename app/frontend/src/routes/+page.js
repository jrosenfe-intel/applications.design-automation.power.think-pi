import { PUBLIC_MASTER_SERVER_IP, PUBLIC_MASTER_SERVER_PORT } from '$env/static/public';


export const load = async ({ fetch }) => {
	const response = await fetch(`${PUBLIC_MASTER_SERVER_IP}:${PUBLIC_MASTER_SERVER_PORT}`);

	return await response.json();
};

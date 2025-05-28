import { useAuth0 } from "@auth0/auth0-react";
import { useEffect } from "react";

const UserSync = () => {
  const { user, getAccessTokenSilently, isAuthenticated } = useAuth0();

  useEffect(() => {
    const syncUser = async () => {
      if (!isAuthenticated || !user) return;

      const syncKey = `user-synced-${user.sub}`;
      const alreadySynced = localStorage.getItem(syncKey);
      if (alreadySynced) return;

      try {
        // const token = await getAccessTokenSilently(); // Uncomment if using Authorization header

        await fetch("http://localhost:5000/api/users/sync", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            // Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            auth0_id: user.sub,
            email: user.email,
            username: user.nickname || user.name || "",
            show_explicit: 1,
            dark_mode: 0,
          }),
        });

        localStorage.setItem(syncKey, "true"); // Mark as synced
        console.log("User synced successfully");
      } catch (err) {
        console.error("Error syncing user:", err);
      }
    };

    syncUser();
  }, [isAuthenticated, user, getAccessTokenSilently]);

  return null;
};

export default UserSync;

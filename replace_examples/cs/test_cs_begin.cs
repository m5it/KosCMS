using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace ExampleApp
{
    public class Program
    {
        public static async Task Main(string[] args)
        {
            Console.WriteLine("C# Application Starting...");
            await RunAsync();
        }
        
        private static async Task RunAsync()
        {
            var service = new UserService();
            var users = await service.GetAllAsync();
            Console.WriteLine($"Found {users.Count} users");
        }
    }
    
    public class UserService
    {
        public async Task<List<User>> GetAllAsync()
        {
            return await Task.FromResult(new List<User>());
        }
    }
    
    public class User
    {
        public string Name { get; set; }
        public int Age { get; set; }
    }
}
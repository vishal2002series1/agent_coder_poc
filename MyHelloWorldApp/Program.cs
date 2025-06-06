using System;

namespace HelloWorldApp
{
    /// <summary>
    /// A simple program that prints "Hello, C#!" to the console.
    /// </summary>
    public class HelloWorldProgram
    {
        /// <summary>
        /// Prints the message "Hello, C#!" to the console.
        /// </summary>
        public static void PrintMessage()
        {
            Console.WriteLine("Hello, C#!");
        }

        /// <summary>
        /// The entry point of the program.
        /// </summary>
        public static void Main(string[] args)
        {
            // Call the method to print the message
            PrintMessage();
        }
    }
}
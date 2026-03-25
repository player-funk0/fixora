export const LANGUAGES = [
  { value: "python",     label: "Python",     ext: ".py"   },
  { value: "javascript", label: "JavaScript", ext: ".js"   },
  { value: "typescript", label: "TypeScript", ext: ".ts"   },
  { value: "cpp",        label: "C++",        ext: ".cpp"  },
  { value: "c",          label: "C",          ext: ".c"    },
  { value: "java",       label: "Java",       ext: ".java" },
  { value: "go",         label: "Go",         ext: ".go"   },
  { value: "rust",       label: "Rust",       ext: ".rs"   },
];

export const EXT_TO_LANGUAGE = {
  ".py":   "python",
  ".js":   "javascript",
  ".ts":   "typescript",
  ".cpp":  "cpp",
  ".cc":   "cpp",
  ".c":    "c",
  ".java": "java",
  ".go":   "go",
  ".rs":   "rust",
};

export const SAMPLE_CODE = {
  python: `def calculate_average(numbers)
    total = 0
    for num in numbers
        total += num
    return total / len(numbers

nums = [10, 20, 30, 40, 50]
print("Average:", calculate_average(nums))`,

  javascript: `async function fetchUser(userId) {
  const response = fetch('/api/users/' + userId)
  const data = response.json()
  if (data.status = 'active') {
    console.log('User: ' + data.name)
    return data
  }
}`,

  typescript: `async function getUser(id: number) {
  const res = fetch(\`/api/users/\${id}\`)
  const data = res.json()
  if (data.active = true) {
    console.log(data.name)
  }
  return data
}`,

  cpp: `#include <iostream>
using namespace std
int main() {
    int nums[] = {1,2,3,4,5}
    int sum = 0
    for (int i = 0; i <= 5; i++)
        sum += nums[i]
    cout << "Sum: " << sum << endl
    return 0
}`,

  java: `public class Main {
    public static void main(String[] args) {
        int[] arr = {1, 2, 3, 4, 5};
        int sum = 0;
        for (int i = 0; i =< arr.length; i++)
            sum += arr[i]
        System.out.println("Sum: " + sum)
    }
}`,

  c: `#include <stdio.h>
int main() {
    int arr[] = {1, 2, 3, 4, 5}
    int sum = 0
    for (int i = 0; i <= 5; i++)
        sum += arr[i]
    printf("Sum: %d\n", sum)
    return 0
}`,

  go: `package main
import "fmt"
func main() {
    nums := []int{1, 2, 3, 4, 5}
    sum := 0
    for i := 0; i =< len(nums); i++ {
        sum += nums[i]
    }
    fmt.Println("Sum:", sum
}`,

  rust: `fn main() {
    let nums = vec![1, 2, 3, 4, 5];
    let mut sum = 0;
    for i in 0..=nums.len() {
        sum += nums[i]
    }
    println!("Sum: {}", sum)
}`,
};
